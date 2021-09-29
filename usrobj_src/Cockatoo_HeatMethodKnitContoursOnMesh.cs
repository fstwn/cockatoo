using System;
using System.Collections;
using System.Collections.Generic;

using Rhino;
using Rhino.Geometry;

using Grasshopper;
using Grasshopper.Kernel;
using Grasshopper.Kernel.Data;
using Grasshopper.Kernel.Types;

using System.Linq;
using System.Threading.Tasks;
using KPlankton;

/// <summary>
/// This class will be instantiated on demand by the Script component.
/// </summary>
public class Script_Instance : GH_ScriptInstance
{
#region Utility functions
  /// <summary>Print a String to the [Out] Parameter of the Script component.</summary>
  /// <param name="text">String to print.</param>
  private void Print(string text) { /* Implementation hidden. */ }
  /// <summary>Print a formatted String to the [Out] Parameter of the Script component.</summary>
  /// <param name="format">String format.</param>
  /// <param name="args">Formatting parameters.</param>
  private void Print(string format, params object[] args) { /* Implementation hidden. */ }
  /// <summary>Print useful information about an object instance to the [Out] Parameter of the Script component. </summary>
  /// <param name="obj">Object instance to parse.</param>
  private void Reflect(object obj) { /* Implementation hidden. */ }
  /// <summary>Print the signatures of all the overloads of a specific method to the [Out] Parameter of the Script component. </summary>
  /// <param name="obj">Object instance to parse.</param>
  private void Reflect(object obj, string method_name) { /* Implementation hidden. */ }
#endregion

#region Members
  /// <summary>Gets the current Rhino document.</summary>
  private readonly RhinoDoc RhinoDocument;
  /// <summary>Gets the Grasshopper document that owns this script.</summary>
  private readonly GH_Document GrasshopperDocument;
  /// <summary>Gets the Grasshopper script component that owns this script.</summary>
  private readonly IGH_Component Component;
  /// <summary>
  /// Gets the current iteration count. The first call to RunScript() is associated with Iteration==0.
  /// Any subsequent call within the same solution will increment the Iteration count.
  /// </summary>
  private readonly int Iteration;
#endregion

  /// <summary>
  /// This procedure contains the user code. Input parameters are provided as regular arguments,
  /// Output parameters as ref arguments. You don't have to assign output parameters,
  /// they will have a default value.
  /// </summary>
  private void RunScript(Mesh ReferenceMesh, System.Object KnitConstraint, List<Polyline> IsoFixGuides, double Threshold, int MaxIterations, int ContourCount, ref object Mesh, ref object Values, ref object Gradient, ref object KnitContours)
  {

    /*
    Original Script by Daniel Piker 03/07/2020
    Modified by Max Eschenbach May 2021
    version 210929
    */

    // set component params
    this.Component.Name = "HeatMethodKnitContoursOnMesh";
    this.Component.NickName = "HMKCOM";
    this.Component.Category = "Cockatoo";
    this.Component.SubCategory = "05 Contouring";
    this.Component.Description = "Constructs contours for deriving a knitting pattern from a mesh using the Heat Method. Use the GuideCurves input to influence the contouring. NOTE: EXPERIMENTAL COMPONENT! Based on a script by Daniel Piker. See: https://discourse.mcneel.com/t/heat-method/105135";

    // set param descriptions
    this.Component.Params.Input[0].Description = "The mesh to create the contours on. {item, mesh}";
    this.Component.Params.Input[1].Description = "The Cockatoo KnitConstraint defining the direction and limits of the contours. {item, KnitConstraint}";
    this.Component.Params.Input[2].Description = "The guide curves for influencing the heat distribution and thus the contour generation. NOTE: Guide Curves must be Polylines and its Vertices must be included in the Mesh! This will be enhanced in a coming update. {list, Polyline}";
    this.Component.Params.Input[3].Description = "The threshold where the heat method will stop iterating. Defaults to 1e-6. {item, double}";
    this.Component.Params.Input[4].Description = "The maximum number of iterations for the internal Heat Method solver. Defaults to 5000. {item, int}";
    this.Component.Params.Input[5].Description = "The number of contour curves to create. Defaults to 20.{item, int}";

    // set defaults
    bool abort = false;
    if (ReferenceMesh == null)
    {
      this.Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
        "Input Parameter ReferenceMesh failed to collect data!");
      abort = true;
    }
    if (KnitConstraint == null)
    {
      this.Component.AddRuntimeMessage(GH_RuntimeMessageLevel.Warning,
        "Input Parameter KnitConstraint failed to collect data!");
      abort = true;
    }
    if (Threshold == 0) Threshold = 1e-6;
    if (MaxIterations == 0) MaxIterations = 5000;
    if (ContourCount == 0) ContourCount = 20;
    if (abort)
    {
      Mesh = new DataTree<Object>();
      Values = new DataTree<Object>();
      Gradient = new DataTree<Object>();
      KnitContours = new DataTree<Object>();
      return;
    }

    // init variables
    double[] values;
    double[][] storedweights;
    int[][] storedneighbours;
    Vector3d[] gradient;
    Vector3d[] edgeGradient;
    int[] fix;
    int[][] equalize;
    Mesh ResultMesh;

    // init vars for threshold tracking
    double heat_avg = 0;
    double poisson_avg = 0;
    bool converged = false;

    // EXTRACT DATA FROM KNITCONSTRAINT ------------------------------------

    dynamic KC = KnitConstraint;
    var StartCourse = KC.start_course;
    var EndCourse = KC.end_course;
    dynamic LeftBoundary = KC.left_boundary;
    dynamic RightBoundary = KC.right_boundary;

    // points of the left boundary are heatpoints
    List<Point3d> HeatPoints = new List<Point3d>();
    foreach (PolylineCurve plc in LeftBoundary)
    {
      Polyline pl = plc.ToPolyline();
      foreach (Point3d pt in pl) HeatPoints.Add(pt);
    }
    Polyline HeatPoly = new Polyline(HeatPoints);
    IsoFixGuides.Add(HeatPoly);

    // points of the right boundary are coldpoints
    List<Point3d> ColdPoints = new List<Point3d>();
    foreach (PolylineCurve plc in RightBoundary)
    {
      Polyline pl = plc.ToPolyline();
      foreach (Point3d pt in pl) ColdPoints.Add(pt);
    }
    Polyline ColdPoly = new Polyline(ColdPoints);
    IsoFixGuides.Add(ColdPoly);

    // INITIALIZE HEAT METHOD -----------------------------------------------

    // convert all quads to triangles
    ReferenceMesh.Faces.ConvertQuadsToTriangles();

    // get kplankton mesh
    KPlanktonMesh ReferencePMesh = KPlankton.RhinoSupport.ToKPlanktonMesh(ReferenceMesh);

    int vc = ReferencePMesh.Vertices.Count;
    storedweights = new double[vc][];
    storedneighbours = new int[vc][];
    values = new double[vc];
    fix = new int[vc];
    equalize = new int[IsoFixGuides.Count][];
    for(int i = 0;i < vc;i++)
    {
      storedweights[i] = ComputeCotanWeights(ReferencePMesh, i);
      storedneighbours[i] = ReferencePMesh.Vertices.GetVertexNeighbours(i);
      for(int j = 0;j < HeatPoints.Count;j++)
      {
        if(ReferencePMesh.Vertices[i].ToPoint3d().DistanceTo(HeatPoints[j]) < Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance)
        {
          values[i] = 1;
          fix[i] = 1;
        }
      }
      for(int j = 0;j < ColdPoints.Count;j++)
      {
        if(ReferencePMesh.Vertices[i].ToPoint3d().DistanceTo(ColdPoints[j]) < Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance)
        {
          values[i] = 0;
          fix[i] = 2;
        }
      }
    }

    for(int i = 0;i < IsoFixGuides.Count;i++)
    {
      Polyline thisPoly = IsoFixGuides[i];
      int polyCount = thisPoly.Count;
      if(thisPoly[thisPoly.Count - 1].Equals(thisPoly[0])) polyCount--;//don't count first point twice for closed curves
      equalize[i] = new int[polyCount];
      for(int j = 0;j < polyCount;j++)
      {
        for(int k = 0;k < vc;k++)
        {
          if(ReferencePMesh.Vertices[k].ToPoint3d().DistanceTo(thisPoly[j]) < Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance)
          {
            equalize[i][j] = k;
            break;
          }
        }
      }
    }

    gradient = new Vector3d[vc];
    ResultMesh = ReferenceMesh.DuplicateMesh();

    edgeGradient = null;

    // HEAT DIFFUSION -----------------------------------------------------

    for(int k = 0; k < MaxIterations; k++)
    {
      double[] newValues = new double[values.Length];
      Parallel.For(0, ReferencePMesh.Vertices.Count,
        i => {

        if(fix[i] == 0)
        {
          int[] neighbours = storedneighbours[i];
          double[] weights = storedweights[i];
          double newValue = 0;
          for(int j = 0;j < neighbours.Length;j++)
          {
            newValue += weights[j] * values[neighbours[j]];
          }
          newValues[i] = newValue;
        }
        else newValues[i] = values[i];
        });

      for(int i = 0; i < equalize.Length; i++)
      {
        double avg = 0;
        for(int j = 0;j < equalize[i].Length;j++)avg += newValues[equalize[i][j]];
        avg /= equalize[i].Length;
        for(int j = 0;j < equalize[i].Length;j++) newValues[equalize[i][j]] = avg;
      }
      values = newValues;

      // track average heat value change
      double this_heat_avg = System.Linq.Enumerable.Average(values);
      double heat_avg_change = Math.Abs(this_heat_avg - heat_avg);
      heat_avg = this_heat_avg;

      if (heat_avg <= Threshold) break;
    }

    double min = values.Min();
    double max = values.Max();
    double mult = 1.0 / (max - min);
    for(int i = 0;i < values.Length;i++) values[i] = mult * (values[i] - min);

    edgeGradient = null;

    // POISSON AVERAGING --------------------------------------------------

    if(edgeGradient == null)
    {
      gradient = ComputeGradients(ReferencePMesh, values);
      double avgGradientLength = 0;
      for(int i = 0;i < gradient.Length;i++)
      {
        avgGradientLength += gradient[i].Length;
      }
      avgGradientLength /= gradient.Length;

      edgeGradient = new Vector3d[ReferencePMesh.Halfedges.Count / 2];
      for(int i = 0;i < ReferencePMesh.Halfedges.Count / 2;i++)
      {
        int start = ReferencePMesh.Halfedges[2 * i].StartVertex;
        int end = ReferencePMesh.Halfedges[(2 * i) + 1].StartVertex;
        Vector3d sv = gradient[start];
        Vector3d ev = gradient[end];
        Vector3d thisEdgeGradient = sv + ev;
        thisEdgeGradient.Unitize();
        thisEdgeGradient *= avgGradientLength;
        edgeGradient[i] = thisEdgeGradient;
      }
    }

    for(int k = 0; k < MaxIterations; k++)
    {
      double[] heChange = new double[ReferencePMesh.Halfedges.Count];
      Parallel.For(0, ReferencePMesh.Halfedges.Count / 2,
        i => {
        int start = ReferencePMesh.Halfedges[2 * i].StartVertex;
        int end = ReferencePMesh.Halfedges[(2 * i) + 1].StartVertex;
        Vector3d edgeVector = ReferencePMesh.Vertices[end].ToPoint3d() - ReferencePMesh.Vertices[start].ToPoint3d();
        double projected = edgeVector * edgeGradient[i];
        double currentDifference = values[end] - values[start];
        double change = currentDifference - projected;
        heChange[2 * i] = 1 * change;
        heChange[(2 * i) + 1] = -1 * change;
        });

      Parallel.For(0, ReferencePMesh.Vertices.Count,
        i => {
        {
          {
            double[] weights = storedweights[i];
            int[] halfedges = ReferencePMesh.Vertices.GetHalfedges(i);
            for(int j = 0;j < halfedges.Length;j++)
            {
              values[i] += heChange[halfedges[j]] * weights[j];
            }
          }
        }
        });

      double this_poisson_avg = 0;
      for(int i = 0;i < equalize.Length;i++)
      {
        double avg = 0;
        for(int j = 0;j < equalize[i].Length;j++)avg += values[equalize[i][j]];
        avg /= equalize[i].Length;
        for(int j = 0;j < equalize[i].Length;j++) values[equalize[i][j]] = avg;
        this_poisson_avg = avg;
      }

      // track average value change for poisson step
      double poisson_avg_change = Math.Abs(this_poisson_avg - poisson_avg);
      poisson_avg = this_poisson_avg;

      if (poisson_avg_change <= Threshold)
      {
        converged = true;
        break;
      }
    }

    this.Component.Message = (converged) ? "Converged" : "MaxIterations reached!";

    // SET TEXTURE COORDINATES ----------------------------------------------

    for(int i = 0;i < ResultMesh.Vertices.Count;i++)
    {
      ResultMesh.TextureCoordinates.SetTextureCoordinate(i, new Point2f(0, (float) (values[i] * 7.0)));
    }

    // CONTOUR GENERATION ----------------------------------------------------

    KnitContours = CreateKnitContours(ResultMesh,
      StartCourse,
      EndCourse,
      HeatPoly.ToPolylineCurve(),
      ColdPoly.ToPolylineCurve(),
      ContourCount - 2);

    // OUTPUT ----------------------------------------------------------------

    // input mesh with adjusted texture coordinates
    Mesh = ResultMesh;
    // the scalar values and gradient vectors per vertex
    Values = values;
    Gradient = gradient;

  }

  // <Custom additional code> 

  private static Vector3d[] ComputeGradients(KPlanktonMesh KPM, double[] values)
  {
    // compute halfedge gradients
    Vector3d[] halfedgeGradients = new Vector3d[KPM.Halfedges.Count];
    for(int i = 0;i < KPM.Halfedges.Count / 2;i++)
    {
      int start = KPM.Halfedges[2 * i].StartVertex;
      int end = KPM.Halfedges[2 * i + 1].StartVertex;
      Vector3d v = KPM.Vertices[end].ToPoint3d() - KPM.Vertices[start].ToPoint3d();
      double lengthSquared = v.SquareLength;
      double diff = values[end] - values[start];
      Vector3d edgeGradient = v * (diff / lengthSquared);
      halfedgeGradients[2 * i] = halfedgeGradients[2 * i + 1] = edgeGradient;
    }

    // compute vertex gradients from halfedge gradients
    Vector3d[] vertexGradients = new Vector3d[KPM.Vertices.Count];
    for(int i = 0;i < KPM.Vertices.Count;i++)
    {
      double[] weights = ComputeCotanWeights(KPM, i);
      Vector3d gradient = new Vector3d();
      int[] halfedges = KPM.Vertices.GetHalfedges(i);
      for(int j = 0;j < halfedges.Length;j++)
      {
        gradient += halfedgeGradients[halfedges[j]] * weights[j];
      }
      vertexGradients[i] = gradient;
    }
    return vertexGradients;
  }

  private static double[] ComputeCotanWeights(KPlanktonMesh KPM, int i)
  {
    int[] Neighbours = KPM.Vertices.GetVertexNeighbours(i);
    Point3d Vertex = KPM.Vertices[i].ToPoint3d();
    int valence = KPM.Vertices.GetValence(i);
    Point3d[] NeighbourPts = new Point3d[valence];
    Vector3d[] Radial = new Vector3d[valence];
    Vector3d[] Around = new Vector3d[valence];
    double[] CotWeight = new double[valence];
    double WeightSum = 0;
    for (int j = 0; j < valence; j++)
    {
      NeighbourPts[j] = KPM.Vertices[Neighbours[j]].ToPoint3d();
      Radial[j] = NeighbourPts[j] - Vertex;
    }
    for (int j = 0; j < valence; j++)
    {
      Around[j] = NeighbourPts[(j + 1) % valence] - NeighbourPts[j];
    }
    int[] halfEdges = KPM.Vertices.GetHalfedges(i);
    for (int j = 0; j < Neighbours.Length; j++)
    {
      int previous = (j + valence - 1) % valence;
      int next = (j + 1) % valence;

      Vector3d Cross1 = Vector3d.CrossProduct(Radial[previous], Around[previous]);
      double Dot1 = Radial[previous] * Around[previous];
      double cwa = Math.Abs(Dot1 / Cross1.Length);

      Vector3d Cross2 = Vector3d.CrossProduct(Radial[next], Around[j]);
      double Dot2 = Radial[next] * Around[j];
      double cwb = Math.Abs(Dot2 / Cross2.Length);

      if(KPM.Halfedges[halfEdges[j]].AdjacentFace == -1){cwa = 0;}
      if(KPM.Halfedges[KPM.Halfedges.GetPairHalfedge(halfEdges[j])].AdjacentFace == -1){cwb = 0;}
      CotWeight[j] = cwa + cwb;
      WeightSum += CotWeight[j];
    }
    for (int j = 0; j < CotWeight.Length; j++) CotWeight[j] /= WeightSum;
    return CotWeight;
  }

  private static Curve[] CreateKnitContours(Mesh M, PolylineCurve SC, PolylineCurve EC, PolylineCurve LB, PolylineCurve RB, int Count)
  {
    // init lists for contours
    Curve[] contours = new Curve[Count + 2];

    // extract gradient from texture coordinates
    double[] values = new double[M.Vertices.Count];
    for(int i = 0;i < M.Vertices.Count;i++) values[i] = M.TextureCoordinates[i].Y;

    // get bounds of gradient value domain
    double min_val = values.Min();
    double max_val = values.Max();

    // compute stepsize for isa values
    double stepsize = (max_val - min_val) / (Count + 1.0);

    // create contours in parallel
    Parallel.For(0, Count,
      j => {
      // compute current iso value
      double iso = min_val + ((j + 1) * stepsize);

      // init list for geometry storage
      List<Curve> curves = new List<Curve>();

      // loop over all faces
      for(int i = 0;i < M.Faces.Count;i++)
      {
        int va = M.Faces[i].A;
        int vb = M.Faces[i].B;
        int vc = M.Faces[i].C;

        double a = M.TextureCoordinates[va].Y - iso;
        double b = M.TextureCoordinates[vb].Y - iso;
        double c = M.TextureCoordinates[vc].Y - iso;

        Point3d pa = M.Vertices.Point3dAt(va);
        Point3d pb = M.Vertices.Point3dAt(vb);
        Point3d pc = M.Vertices.Point3dAt(vc);

        List<Point3d> ends = new List<Point3d>();

        // find line segment
        if(a < 0 != b < 0)
        {
          double wa = b / (b - a);
          double wb = 1 - wa;
          ends.Add(wa * pa + wb * pb);
        }
        if(a < 0 != c < 0)
        {
          double wa = c / (c - a);
          double wc = 1 - wa;
          ends.Add(wa * pa + wc * pc);
        }
        if(c < 0 != b < 0)
        {
          double wb = c / (c - b);
          double wc = 1 - wb;
          ends.Add(wb * pb + wc * pc);
        }

        // if line segment is complete add it to list
        if(ends.Count == 2)
        {
          curves.Add(new Line(ends[0], ends[1]).ToNurbsCurve());
        }
      }

      // insert contour into array
      contours[j + 1] = Rhino.Geometry.Curve.JoinCurves(curves)[0];
      // end parallel for
      });

    // insert left and right boundary
    Array.Reverse(contours);
    contours[0] = LB;
    contours[Count + 1] = RB;

    // unify direction of contour curves
    for (int i = 0; i < contours.Count(); i++)
    {
      double scpt;
      SC.ClosestPoint(contours[i].PointAtStart, out scpt);
      Point3d scp = SC.PointAt(scpt);
      if (contours[i].PointAtStart.DistanceTo(scp) > Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance) contours[i].Reverse();
    }
    return contours;
  }

  // </Custom additional code> 
}