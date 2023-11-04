using System;
using System.IO;
using System.Text;

using Rhino;
using Rhino.PlugIns;

namespace RhinoCodePlatform.Rhino3D.Projects.Plugin
{
  public class ProjectPlugin : PlugIn
  {
    public static string DecryptString(string text)
    {
      if (text is null)
        throw new ArgumentNullException(nameof(text));

      if (string.IsNullOrWhiteSpace(text))
        return string.Empty;

      return Encoding.UTF8.GetString(Convert.FromBase64String(text));
    }

    protected override LoadReturnCode OnLoad(ref string errorMessage)
    {
      var result = base.OnLoad(ref errorMessage);

      string message = "Copyright © 2023 Chris Mackey";
      if (!string.IsNullOrWhiteSpace(message))
      {
        Rhino.RhinoApp.WriteLine(message);
      }

      return result;
    }
  }
}

