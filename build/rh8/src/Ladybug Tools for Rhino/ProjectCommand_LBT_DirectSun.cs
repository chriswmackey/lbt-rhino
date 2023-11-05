using System;

using Rhino;
using Rhino.Commands;

namespace RhinoCodePlatform.Rhino3D.Projects.Plugin
{
  [CommandStyle(Rhino.Commands.Style.ScriptRunner)]
  public class ProjectCommand_LBT_DirectSun : Command
  {
    public Guid CommandId { get; } = new Guid("5853c1ed-e530-4544-a65a-8cc5e4da8976");

    public ProjectCommand_LBT_DirectSun() { Instance = this; }

    public static ProjectCommand_LBT_DirectSun Instance { get; private set; }

    public override string EnglishName => "LBT_DirectSun";

    protected override Rhino.Commands.Result RunCommand(RhinoDoc doc, RunMode mode)
        => ProjectPlugin.RunCode(this, CommandId, doc, mode);
  }
}
