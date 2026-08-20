using System.Threading.Tasks;
using BankMigrate.Api.Models;
using BankMigrate.Api.Services;
using Microsoft.AspNetCore.Mvc;

namespace BankMigrate.Api.Controllers
{
    [ApiController]
    [Route("api/migrations")]
    public class MigrationController : ControllerBase
    {
        private readonly IMigrationService _migrationService;
        private readonly IReportingService _reportingService;

        public MigrationController(IMigrationService migrationService, IReportingService reportingService)
        {
            _migrationService = migrationService;
            _reportingService = reportingService;
        }

        /// <summary>
        /// POST /api/migrations - Starts a new migration run (triggers Python engine)
        /// </summary>
        [HttpPost]
        public async Task<IActionResult> StartMigration([FromBody] StartMigrationRequest? request)
        {
            var response = await _migrationService.StartMigrationRunAsync(request?.RunId);
            return Ok(response);
        }

        /// <summary>
        /// GET /api/migrations - Lists past and current migration runs
        /// </summary>
        [HttpGet]
        public async Task<IActionResult> GetAllRuns()
        {
            var runs = await _reportingService.GetAllRunsAsync();
            return Ok(runs);
        }

        /// <summary>
        /// GET /api/migrations/{runId} - Gets status and details of one run
        /// </summary>
        [HttpGet("{runId}")]
        public async Task<IActionResult> GetRunById(string runId)
        {
            var run = await _reportingService.GetRunByIdAsync(runId);
            if (run == null)
            {
                return NotFound(new { Message = $"Migration run '{runId}' not found." });
            }
            return Ok(run);
        }

        /// <summary>
        /// GET /api/migrations/{runId}/exceptions - Lists rejected records for a run
        /// </summary>
        [HttpGet("{runId}/exceptions")]
        public async Task<IActionResult> GetRunExceptions(string runId)
        {
            var exceptions = await _reportingService.GetExceptionsByRunIdAsync(runId);
            return Ok(exceptions);
        }

        /// <summary>
        /// GET /api/migrations/{runId}/reconciliation - Gets the reconciliation report for a run
        /// </summary>
        [HttpGet("{runId}/reconciliation")]
        public async Task<IActionResult> GetRunReconciliation(string runId)
        {
            var report = await _reportingService.GetReconciliationByRunIdAsync(runId);
            if (report == null)
            {
                return NotFound(new { Message = $"Reconciliation report for run '{runId}' not found." });
            }
            return Ok(report);
        }

        /// <summary>
        /// POST /api/migrations/{runId}/retry - Retries a failed or partially completed run
        /// </summary>
        [HttpPost("{runId}/retry")]
        public async Task<IActionResult> RetryRun(string runId)
        {
            var response = await _migrationService.RetryMigrationRunAsync(runId);
            return Ok(response);
        }
    }
}
