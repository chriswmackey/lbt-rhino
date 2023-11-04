using System;

using Rhino;
using Rhino.Commands;

namespace RhinoCodePlatform.Rhino3D.Projects.Plugin
{
  [CommandStyle(Rhino.Commands.Style.ScriptRunner)]
  public class ProjectCommand_LBT_Sunpath : Command
  {
    public Guid CommandId { get; } = new Guid("0566725e-a8ae-4419-8d94-4d0c6910c256");

    public ProjectCommand_LBT_Sunpath() { Instance = this; }

    public static ProjectCommand_LBT_Sunpath Instance { get; private set; }

    public override string EnglishName => "LBT_Sunpath";

    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc, RunMode mode)
        => ProjectPlugin.RunCode(this, CommandId, doc, mode);
  }
}
