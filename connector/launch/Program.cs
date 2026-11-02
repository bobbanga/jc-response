using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;

internal static class Program
{
    const string ZipUrl = "https://github.com/bobbanga/jc-response/releases/download/v1.2.0-r1/JC_response-windows-x64-1.2.0-r1.zip";
    const long ZipSize = 122270089L;
    const string ZipSha = "91b6df6dd4ae0ee4684c8d4946956ca2599294e118014837f3a339bb717be713";
    const string ExeSha = "d665c71273a99eddab01dcd38f6cd8d192a4d42b3bdf4be0e1da26f228cf810d";
    const string ProgramVersion = "1.2.0";
    const string Contract = "response_flow/1.1";

    static readonly string[] DocFiles = new string[]
    {
        "docs/安装说明.md",
        "docs/使用说明.md",
        "docs/安全说明.md",
        "docs/接入提示词.md",
        "docs/升级说明.md",
        "skills/jc-response-preview/SKILL.md",
        "VERSION",
        "RELEASE-METADATA.json",
        "SHA256SUMS.txt"
    };

    static int Main(string[] args)
    {
        try
        {
            ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072 | (SecurityProtocolType)768;
        }
        catch (NotSupportedException)
        {
        }
        bool install = false;
        bool refresh = false;
        for (int i = 0; i < args.Length; i++)
        {
            if (args[i] == "--install-confirmed") install = true;
            else if (args[i] == "--refresh-docs-confirmed") refresh = true;
            else
            {
                Console.Error.WriteLine("unknown_argument");
                return 2;
            }
        }
        if (!install && !refresh) return Launch();
        return Maintain(install, refresh);
    }

    static int Launch()
    {
        string reason;
        string exe = LocateMatchingExe(out reason);
        if (exe == null)
        {
            Console.Error.WriteLine(reason);
            Console.Error.WriteLine("download_url=" + ZipUrl);
            Console.Error.WriteLine("file_size=" + ZipSize.ToString());
            Console.Error.WriteLine("sha256=" + ZipSha);
            Console.Error.WriteLine("not_downloaded");
            return 2;
        }
        return Passthrough(exe);
    }

    static int Maintain(bool install, bool refresh)
    {
        string local = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        if (string.IsNullOrEmpty(local))
        {
            Console.Error.WriteLine("localappdata_missing");
            return 2;
        }
        string program = Path.Combine(local, "Programs", "JC_response");
        if (IsReparse(program) || DirectoryHasDatabase(program))
        {
            Console.Error.WriteLine("program_dir_rejected");
            return 2;
        }
        string exe = Path.Combine(program, "bin", "jctrans-mcp.exe");
        bool present = File.Exists(exe) && !IsReparse(exe);
        if (present)
        {
            string reason;
            if (LocateMatchingExe(out reason) == null)
            {
                Console.Error.WriteLine(reason);
                Console.Error.WriteLine("not_downloaded");
                return 2;
            }
            if (!refresh)
            {
                Console.Error.WriteLine("install_status=already_installed");
                Console.Error.WriteLine("docs_not_copied");
                return 0;
            }
            return RefreshDocs(program);
        }
        if (Directory.Exists(program) && Directory.GetFileSystemEntries(program).Length > 0)
        {
            Console.Error.WriteLine("unknown_program_dir");
            Console.Error.WriteLine("not_downloaded");
            return 2;
        }
        if (!install)
        {
            Console.Error.WriteLine("not_installed");
            Console.Error.WriteLine("not_downloaded");
            return 2;
        }
        return DownloadAndInstall();
    }

    static string LocateMatchingExe(out string reason)
    {
        reason = "not_installed";
        if (!PinMatches())
        {
            reason = "runtime_pin_mismatch";
            return null;
        }
        string local = Environment.GetEnvironmentVariable("LOCALAPPDATA");
        if (string.IsNullOrEmpty(local))
        {
            reason = "localappdata_missing";
            return null;
        }
        string program = Path.Combine(local, "Programs", "JC_response");
        string exe = Path.Combine(program, "bin", "jctrans-mcp.exe");
        if (IsReparse(program) || IsReparse(exe) || DirectoryHasDatabase(program))
        {
            reason = "program_dir_rejected";
            return null;
        }
        if (!File.Exists(exe)) return null;
        string version;
        string contract;
        if (!ReadVersion(Path.Combine(program, "VERSION"), out version, out contract)
            || version != ProgramVersion || contract != Contract)
        {
            reason = "version_rejected";
            return null;
        }
        if (!HashEquals(exe, ExeSha))
        {
            reason = "exe_hash_mismatch";
            return null;
        }
        reason = "";
        return exe;
    }

    static bool PinMatches()
    {
        string path = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "runtime-pin.json");
        if (!File.Exists(path)) return false;
        Dictionary<string, object> pin = ParseObject(File.ReadAllText(path, Encoding.UTF8));
        if (pin == null) return false;
        return Text(pin, "download_url") == ZipUrl
            && Text(pin, "sha256") == ZipSha
            && Text(pin, "exe_sha256") == ExeSha
            && Text(pin, "program_version") == ProgramVersion
            && Text(pin, "contract") == Contract
            && Long(pin, "file_size") == ZipSize;
    }

    static int DownloadAndInstall()
    {
        string root = Path.Combine(Path.GetTempPath(), "jc-response-market-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        string zip = Path.Combine(root, "package.zip");
        string extract = Path.Combine(root, "extract");
        try
        {
            string error = Download(zip);
            if (error != null)
            {
                Console.Error.WriteLine(error);
                return 3;
            }
            if (!ExtractSafe(zip, extract))
            {
                Console.Error.WriteLine("extract_rejected");
                return 3;
            }
            if (!ReleaseExesMatch(extract))
            {
                Console.Error.WriteLine("release_exe_mismatch");
                return 3;
            }
            string installer = Path.Combine(extract, "bin", "JC_response.exe");
            var info = new ProcessStartInfo();
            info.FileName = installer;
            info.Arguments = "--install-user --json";
            info.WorkingDirectory = extract;
            info.UseShellExecute = false;
            info.CreateNoWindow = true;
            info.RedirectStandardOutput = true;
            info.RedirectStandardError = true;
            Process process = Process.Start(info);
            var stdout = new StringBuilder();
            process.OutputDataReceived += delegate(object sender, DataReceivedEventArgs e)
            {
                if (e.Data != null) stdout.AppendLine(e.Data);
            };
            process.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) { };
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            if (!process.WaitForExit(240000))
            {
                process.Kill();
                Console.Error.WriteLine("install_status=timeout");
                return 2;
            }
            process.WaitForExit();
            string status = StatusOf(stdout.ToString());
            Console.Error.WriteLine("install_status=" + status);
            if (status == "installed" || status == "already_installed" || status == "upgraded") return 0;
            return 2;
        }
        finally
        {
            try { Directory.Delete(root, true); } catch (IOException) { }
        }
    }

    static int RefreshDocs(string program)
    {
        string root = Path.Combine(Path.GetTempPath(), "jc-response-market-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        string zip = Path.Combine(root, "package.zip");
        string extract = Path.Combine(root, "extract");
        var backups = new List<string>();
        try
        {
            string error = Download(zip);
            if (error != null)
            {
                Console.Error.WriteLine(error);
                return 3;
            }
            if (!ExtractSafe(zip, extract) || !BinsMatch(Path.Combine(extract, "bin"), Path.Combine(program, "bin")))
            {
                Console.Error.WriteLine("bin_mismatch");
                Console.Error.WriteLine("docs_not_copied");
                return 2;
            }
            for (int i = 0; i < DocFiles.Length; i++)
            {
                string relative = DocFiles[i].Replace('/', Path.DirectorySeparatorChar);
                string source = Path.Combine(extract, relative);
                string target = Path.Combine(program, relative);
                if (IsReparse(source) || IsReparse(target) || IsReparse(Path.GetDirectoryName(target)))
                {
                    Restore(backups);
                    Console.Error.WriteLine("docs_rejected");
                    return 2;
                }
                if (!File.Exists(source))
                {
                    Restore(backups);
                    Console.Error.WriteLine("docs_source_missing");
                    return 2;
                }
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                string backup = target + ".market-bak";
                string temp = target + ".market-tmp";
                try
                {
                    if (File.Exists(target))
                    {
                        File.Copy(target, backup, true);
                        backups.Add(target);
                    }
                    File.Copy(source, temp, true);
                    if (File.Exists(target)) File.Replace(temp, target, null);
                    else File.Move(temp, target);
                }
                catch (IOException)
                {
                    if (File.Exists(temp)) File.Delete(temp);
                    Restore(backups);
                    Console.Error.WriteLine("docs_locked");
                    return 2;
                }
                catch (UnauthorizedAccessException)
                {
                    if (File.Exists(temp)) File.Delete(temp);
                    Restore(backups);
                    Console.Error.WriteLine("docs_locked");
                    return 2;
                }
            }
            Console.Error.WriteLine("docs_refreshed=" + DocFiles.Length.ToString());
            return 0;
        }
        finally
        {
            for (int i = 0; i < backups.Count; i++)
            {
                string backup = backups[i] + ".market-bak";
                if (File.Exists(backup)) File.Delete(backup);
            }
            try { Directory.Delete(root, true); } catch (IOException) { }
        }
    }

    static void Restore(List<string> backups)
    {
        for (int i = backups.Count - 1; i >= 0; i--)
        {
            string target = backups[i];
            string backup = target + ".market-bak";
            if (File.Exists(backup)) File.Copy(backup, target, true);
        }
    }

    static string Download(string destination)
    {
        string current = ZipUrl;
        for (int hop = 0; hop < 5; hop++)
        {
            Uri uri;
            if (!Uri.TryCreate(current, UriKind.Absolute, out uri) || uri.Scheme != Uri.UriSchemeHttps || !AllowedHost(uri.Host))
                return "download_rejected host=" + (uri == null ? current : uri.Host);
            var request = (HttpWebRequest)WebRequest.Create(uri);
            request.AllowAutoRedirect = false;
            request.UserAgent = "JC-Response-market/1.0.0";
            request.Timeout = 120000;
            string proxy = Environment.GetEnvironmentVariable("HTTPS_PROXY");
            if (string.IsNullOrEmpty(proxy)) proxy = Environment.GetEnvironmentVariable("https_proxy");
            if (!string.IsNullOrEmpty(proxy)) request.Proxy = new WebProxy(proxy);
            HttpWebResponse response;
            try { response = (HttpWebResponse)request.GetResponse(); }
            catch (WebException) { return "download_failed"; }
            int code = (int)response.StatusCode;
            if (code >= 300 && code < 400)
            {
                string next = response.Headers["Location"];
                response.Close();
                if (string.IsNullOrEmpty(next)) return "download_rejected";
                current = next;
                continue;
            }
            if (code != 200)
            {
                response.Close();
                return "download_failed";
            }
            using (response)
            using (Stream input = response.GetResponseStream())
            using (var output = new FileStream(destination, FileMode.Create, FileAccess.Write, FileShare.None))
            {
                var buffer = new byte[81920];
                long total = 0;
                int read;
                while ((read = input.Read(buffer, 0, buffer.Length)) > 0)
                {
                    total += read;
                    if (total > ZipSize)
                    {
                        output.Close();
                        File.Delete(destination);
                        return "download_too_large";
                    }
                    output.Write(buffer, 0, read);
                }
            }
            if (new FileInfo(destination).Length != ZipSize || !HashEquals(destination, ZipSha))
            {
                File.Delete(destination);
                return "download_hash_mismatch";
            }
            return null;
        }
        return "download_rejected";
    }

    static bool AllowedHost(string host)
    {
        string name = host.ToLowerInvariant();
        return name == "github.com"
            || name == "objects.githubusercontent.com"
            || name == "release-assets.githubusercontent.com"
            || name == "github-releases.githubusercontent.com";
    }

    static bool ExtractSafe(string zipPath, string destination)
    {
        Directory.CreateDirectory(destination);
        string root = Path.GetFullPath(destination).TrimEnd(Path.DirectorySeparatorChar) + Path.DirectorySeparatorChar;
        using (ZipArchive zip = ZipFile.OpenRead(zipPath))
        {
            foreach (ZipArchiveEntry entry in zip.Entries)
            {
                string name = entry.FullName.Replace('\\', '/');
                if (name.Length == 0 || name.StartsWith("/") || name.IndexOf("..", StringComparison.Ordinal) >= 0 || name.IndexOf(':') >= 0)
                    return false;
                if (((entry.ExternalAttributes >> 16) & 0xF000) == 0xA000) return false;
                string target = Path.GetFullPath(Path.Combine(destination, name.Replace('/', Path.DirectorySeparatorChar)));
                if (!target.StartsWith(root, StringComparison.OrdinalIgnoreCase) && !target.Equals(root.TrimEnd(Path.DirectorySeparatorChar), StringComparison.OrdinalIgnoreCase))
                    return false;
                if (name.EndsWith("/"))
                {
                    Directory.CreateDirectory(target);
                    continue;
                }
                if (IsReparse(target)) return false;
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                entry.ExtractToFile(target, false);
            }
        }
        return true;
    }

    static bool ReleaseExesMatch(string extract)
    {
        return HashEquals(Path.Combine(extract, "bin", "JC_response.exe"), ExeSha)
            && HashEquals(Path.Combine(extract, "bin", "jctrans.exe"), ExeSha)
            && HashEquals(Path.Combine(extract, "bin", "jctrans-mcp.exe"), ExeSha);
    }

    static bool BinsMatch(string left, string right)
    {
        Dictionary<string, string> a = BinHashes(left);
        Dictionary<string, string> b = BinHashes(right);
        if (a == null || b == null || a.Count != b.Count) return false;
        foreach (KeyValuePair<string, string> pair in a)
        {
            string other;
            if (!b.TryGetValue(pair.Key, out other) || other != pair.Value) return false;
        }
        return true;
    }

    static Dictionary<string, string> BinHashes(string root)
    {
        var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        if (!Directory.Exists(root) || IsReparse(root)) return null;
        foreach (string file in Directory.GetFiles(root, "*", SearchOption.AllDirectories))
        {
            if (IsReparse(file)) return null;
            string relative = file.Substring(root.Length).TrimStart(Path.DirectorySeparatorChar).Replace('\\', '/');
            result[relative] = Sha256(file);
        }
        return result;
    }

    static int Passthrough(string exe)
    {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job != IntPtr.Zero)
        {
            var limits = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
            limits.BasicLimitInformation.LimitFlags = 0x2000;
            int length = Marshal.SizeOf(typeof(JOBOBJECT_EXTENDED_LIMIT_INFORMATION));
            IntPtr pointer = Marshal.AllocHGlobal(length);
            try
            {
                Marshal.StructureToPtr(limits, pointer, false);
                SetInformationJobObject(job, 9, pointer, (uint)length);
            }
            finally
            {
                Marshal.FreeHGlobal(pointer);
            }
        }
        var startup = new STARTUPINFO();
        startup.cb = Marshal.SizeOf(typeof(STARTUPINFO));
        startup.dwFlags = 0x100;
        startup.hStdInput = GetStdHandle(-10);
        startup.hStdOutput = GetStdHandle(-11);
        startup.hStdError = GetStdHandle(-12);
        PROCESS_INFORMATION process;
        if (!CreateProcess(exe, null, IntPtr.Zero, IntPtr.Zero, true, 0, IntPtr.Zero, null, ref startup, out process))
        {
            Console.Error.WriteLine("spawn_failed");
            return 2;
        }
        if (job != IntPtr.Zero) AssignProcessToJobObject(job, process.hProcess);
        WaitForSingleObject(process.hProcess, 0xFFFFFFFF);
        uint code;
        GetExitCodeProcess(process.hProcess, out code);
        CloseHandle(process.hThread);
        CloseHandle(process.hProcess);
        return (int)code;
    }

    static bool ReadVersion(string path, out string version, out string contract)
    {
        version = "";
        contract = "";
        if (!File.Exists(path) || IsReparse(path)) return false;
        string[] lines = File.ReadAllLines(path, Encoding.UTF8);
        for (int i = 0; i < lines.Length; i++)
        {
            if (lines[i].StartsWith("version=")) version = lines[i].Substring("version=".Length).Trim();
            if (lines[i].StartsWith("schema=")) contract = lines[i].Substring("schema=".Length).Trim();
        }
        return version.Length > 0 && contract.Length > 0;
    }

    static bool DirectoryHasDatabase(string root)
    {
        if (!Directory.Exists(root)) return false;
        return Directory.GetFiles(root, "*.db", SearchOption.AllDirectories).Length > 0;
    }

    static bool IsReparse(string path)
    {
        try
        {
            if (string.IsNullOrEmpty(path) || !File.Exists(path) && !Directory.Exists(path)) return false;
            return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0;
        }
        catch (IOException) { return true; }
        catch (UnauthorizedAccessException) { return true; }
    }

    static bool HashEquals(string path, string expected)
    {
        if (!File.Exists(path) || IsReparse(path)) return false;
        return string.Equals(Sha256(path), expected, StringComparison.OrdinalIgnoreCase);
    }

    static string Sha256(string path)
    {
        using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        using (SHA256 sha = SHA256.Create())
        {
            byte[] hash = sha.ComputeHash(stream);
            var builder = new StringBuilder(hash.Length * 2);
            for (int i = 0; i < hash.Length; i++) builder.Append(hash[i].ToString("x2"));
            return builder.ToString();
        }
    }

    static string StatusOf(string output)
    {
        Dictionary<string, object> obj = ParseObject(output);
        string status = Text(obj, "status");
        return status.Length == 0 ? "unreadable" : status;
    }

    static Dictionary<string, object> ParseObject(string text)
    {
        if (string.IsNullOrEmpty(text)) return null;
        int start = text.IndexOf('{');
        int end = text.LastIndexOf('}');
        if (start < 0 || end <= start) return null;
        try
        {
            var serializer = new JavaScriptSerializer();
            return serializer.DeserializeObject(text.Substring(start, end - start + 1)) as Dictionary<string, object>;
        }
        catch (ArgumentException) { return null; }
        catch (InvalidOperationException) { return null; }
    }

    static string Text(Dictionary<string, object> obj, string key)
    {
        if (obj == null || !obj.ContainsKey(key) || obj[key] == null) return "";
        return obj[key].ToString();
    }

    static long Long(Dictionary<string, object> obj, string key)
    {
        if (obj == null || !obj.ContainsKey(key) || obj[key] == null) return -1;
        long value;
        return long.TryParse(obj[key].ToString(), out value) ? value : -1;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool CreateProcess(string application, string command, IntPtr processAttributes, IntPtr threadAttributes, bool inherit, uint flags, IntPtr environment, string directory, ref STARTUPINFO startup, out PROCESS_INFORMATION process);
    [DllImport("kernel32.dll")]
    static extern IntPtr GetStdHandle(int handle);
    [DllImport("kernel32.dll")]
    static extern uint WaitForSingleObject(IntPtr handle, uint milliseconds);
    [DllImport("kernel32.dll")]
    static extern bool GetExitCodeProcess(IntPtr process, out uint code);
    [DllImport("kernel32.dll")]
    static extern bool CloseHandle(IntPtr handle);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode)]
    static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll")]
    static extern bool SetInformationJobObject(IntPtr job, int infoClass, IntPtr info, uint length);
    [DllImport("kernel32.dll")]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    struct STARTUPINFO
    {
        public int cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        public int dwX;
        public int dwY;
        public int dwXSize;
        public int dwYSize;
        public int dwXCountChars;
        public int dwYCountChars;
        public int dwFillAttribute;
        public int dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public int dwProcessId;
        public int dwThreadId;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct IO_COUNTERS
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }
}
