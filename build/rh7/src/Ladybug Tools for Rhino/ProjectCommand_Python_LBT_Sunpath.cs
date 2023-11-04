using System;

using Rhino.Commands;

namespace RhinoCodePlatform.Rhino3D.Projects.Plugin
{
  [CommandStyle(Rhino.Commands.Style.ScriptRunner)]
  public class ProjectCommand_Python_LBT_Sunpath  : Command
  {
    Rhino.Runtime.PythonScript _script;
    Rhino.Runtime.PythonCompiledCode _compiledCode;

    public Guid CommandId { get; } = new Guid("0566725e-a8ae-4419-8d94-4d0c6910c256");

    public override string EnglishName => "LBT_Sunpath";

    protected override Rhino.Commands.Result RunCommand(Rhino.RhinoDoc doc, Rhino.Commands.RunMode mode)
    {
      if (_compiledCode is null)
      {
        ProjectLibs.InitPythonLibraries();

        _script = Rhino.Runtime.PythonScript.Create();
        _compiledCode = _script.Compile(
            ProjectPlugin.DecryptString("IyEgcHl0aG9uIDINCmltcG9ydCBvcw0KaW1wb3J0IG1hdGgNCg0KdHJ5Og0KICAgIGZyb20gbGFkeWJ1Z19nZW9tZXRyeS5nZW9tZXRyeTJkIGltcG9ydCBQb2ludDJEDQogICAgZnJvbSBsYWR5YnVnX2dlb21ldHJ5Lmdlb21ldHJ5M2QgaW1wb3J0IFBvaW50M0QsIFZlY3RvcjNEDQpleGNlcHQgSW1wb3J0RXJyb3IgYXMgZToNCiAgICByYWlzZSBJbXBvcnRFcnJvcignXG5GYWlsZWQgdG8gaW1wb3J0IGxhZHlidWdfZ2VvbWV0cnk6XG5cdHt9Jy5mb3JtYXQoZSkpDQoNCnRyeToNCiAgICBmcm9tIGxhZHlidWcuZXB3IGltcG9ydCBFUFcNCiAgICBmcm9tIGxhZHlidWcuc3VucGF0aCBpbXBvcnQgU3VucGF0aA0KZXhjZXB0IEltcG9ydEVycm9yIGFzIGU6DQogICAgcmFpc2UgSW1wb3J0RXJyb3IoJ1xuRmFpbGVkIHRvIGltcG9ydCBsYWR5YnVnOlxuXHR7fScuZm9ybWF0KGUpKQ0KDQp0cnk6DQogICAgZnJvbSBsYWR5YnVnX3JoaW5vLmNvbmZpZyBpbXBvcnQgY29udmVyc2lvbl90b19tZXRlcnMNCiAgICBmcm9tIGxhZHlidWdfcmhpbm8uYmFrZW9iamVjdHMgaW1wb3J0IGJha2VfdmlzdWFsaXphdGlvbl9zZXQNCmV4Y2VwdCBJbXBvcnRFcnJvciBhcyBlOg0KICAgIHJhaXNlIEltcG9ydEVycm9yKCdcbkZhaWxlZCB0byBpbXBvcnQgbGFkeWJ1Z19yaGlubzpcblx0e30nLmZvcm1hdChlKSkNCg0KaW1wb3J0IHJoaW5vc2NyaXB0c3ludGF4IGFzIHJzDQoNCg0KZGVmIHJ1bl9zdW5wYXRoX2NvbW1hbmQoKToNCiAgICAjIGdldCB0aGUgRVBXDQogICAgZXB3X3BhdGggPSBycy5HZXRTdHJpbmcoJ1NlbGVjdCBBbiBFUFcgRmlsZSBQYXRoJykNCiAgICBpZiBub3QgZXB3X3BhdGg6DQogICAgICAgIHJldHVybg0KICAgIGlmIG5vdCBvcy5wYXRoLmlzZmlsZShlcHdfcGF0aCk6DQogICAgICAgIHByaW50KCdTZWxlY3RlZCBFUFcgZmlsZSBhdCBkb2VzIG5vdCBleGlzdCBhdDoge30nLmZvcm1hdChlcHdfcGF0aCkpDQogICAgICAgIHJldHVybg0KICAgIA0KDQogICAgIyBwcm9jZXNzIGFsbCBvZiB0aGUgZ2xvYmFsIGlucHV0cyBmb3IgdGhlIHN1bnBhdGgNCiAgICBub3J0aF8gPSAwDQogICAgY2VudGVyX3B0LCBjZW50ZXJfcHQzZCA9IFBvaW50MkQoKSwgUG9pbnQzRCgpDQogICAgeiA9IDANCiAgICBfc2NhbGVfID0gMQ0KICAgIHJhZGl1cyA9ICgxMDAgKiBfc2NhbGVfKSAvIGNvbnZlcnNpb25fdG9fbWV0ZXJzKCkNCiAgICBzb2xhcl90aW1lXyA9IEZhbHNlDQogICAgZGFpbHlfID0gRmFsc2UNCiAgICBwcm9qZWN0aW9uXyA9IE5vbmUNCiAgICBkbF9zYXZpbmdfID0gTm9uZQ0KICAgIGxfcGFyID0gTm9uZQ0KICAgIGhveXNfID0gW10NCiAgICBkYXRhXyA9IFtdDQoNCiAgICAjIGdldCB0aGUgbG9jYXRpb24gZnJvbSB0aGUgRVBXDQogICAgZXB3X29iaiA9IEVQVyhlcHdfcGF0aCkNCiAgICBfbG9jYXRpb24gPSBlcHdfb2JqLmxvY2F0aW9uDQoNCiAgICAjIG1ha2UgdGhlIHN1bnBhdGgNCiAgICBzcCA9IFN1bnBhdGguZnJvbV9sb2NhdGlvbihfbG9jYXRpb24sIG5vcnRoXywgZGxfc2F2aW5nXykNCiAgICB2aXNfc2V0X2FyZ3MgPSBbaG95c18sIGRhdGFfLCBsX3BhciwgcmFkaXVzLCBjZW50ZXJfcHQzZCwgc29sYXJfdGltZV8sIGRhaWx5XywgcHJvamVjdGlvbl9dDQogICAgdmlzX3NldCA9IHNwLnRvX3Zpc19zZXQoKnZpc19zZXRfYXJncykNCiAgICBiYWtlX3Zpc3VhbGl6YXRpb25fc2V0KHZpc19zZXQpDQoNCg0KcnVuX3N1bnBhdGhfY29tbWFuZCgpDQo=")
          );
      }

      if (_compiledCode is null)
      {
        Rhino.RhinoApp.WriteLine("The script code for {0} could not be retrieved or compiled.", EnglishName);
        return Rhino.Commands.Result.Failure;
      }

      _script.ScriptContextDoc = doc;
      _script.SetVariable("__name__", "__main__");

      _compiledCode.Execute(_script);

      return Rhino.Commands.Result.Success;
    }
  }
}
