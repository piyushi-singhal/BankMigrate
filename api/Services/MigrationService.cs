using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using BankMigrate.Api.Models;

namespace BankMigrate.Api.Services
{
    public interface IMigrationService
    {
        Task<StartMigrationResponse> StartMigrationRunAsync(string? requestedRunId = null);
        Task<StartMigrationResponse> RetryMigrationRunAsync(string runId);
    }

    public class MigrationService : IMigrationService
    {
        private readonly string _projectRoot;
        private readonly string _pythonExecutable;

        public MigrationService()
        {
            // Resolve path to Python virtual environment
            _projectRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", ".."));
            _pythonExecutable = Path.Combine(_projectRoot, "venv", "bin", "python");

            if (!File.Exists(_pythonExecutable))
            {
                _pythonExecutable = "python3";
            }
        }

        public Task<StartMigrationResponse> StartMigrationRunAsync(string? requestedRunId = null)
        {
            var runId = requestedRunId ?? $"RUN-{DateTime.UtcNow:yyyyMMdd-HHmmss}";

            var psi = new ProcessStartInfo
            {
                FileName = _pythonExecutable,
                Arguments = $"-m migration_engine.pipeline --run-id {runId}",
                WorkingDirectory = _projectRoot,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            psi.EnvironmentVariables["PYTHONPATH"] = _projectRoot;

            Task.Run(() =>
            {
                try
                {
                    using var proc = Process.Start(psi);
                    if (proc != null)
                    {
                        proc.WaitForExit();
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error triggering Python pipeline process: {ex.Message}");
                }
            });

            return Task.FromResult(new StartMigrationResponse
            {
                RunId = runId,
                Message = "Migration run triggered successfully.",
                Status = "IN_PROGRESS"
            });
        }

        public Task<StartMigrationResponse> RetryMigrationRunAsync(string runId)
        {
            return StartMigrationRunAsync(runId);
        }
    }
}
