using System;
using System.Collections.Generic;
using System.Data;
using System.Threading.Tasks;
using BankMigrate.Api.Models;
using Dapper;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.Configuration;

namespace BankMigrate.Api.Services
{
    public interface IReportingService
    {
        Task<IEnumerable<MigrationRunDto>> GetAllRunsAsync();
        Task<MigrationRunDto?> GetRunByIdAsync(string runId);
        Task<IEnumerable<ExceptionDto>> GetExceptionsByRunIdAsync(string runId);
        Task<ReconciliationReportDto?> GetReconciliationByRunIdAsync(string runId);
    }

    public class ReportingService : IReportingService
    {
        private readonly string _connectionString;

        public ReportingService(IConfiguration configuration)
        {
            _connectionString = configuration.GetConnectionString("BankMigrateTarget")
                ?? "Server=localhost,1433;Database=BankMigrate_Target;User Id=sa;Password=BankMigrate123!;TrustServerCertificate=True;";
        }

        private IDbConnection CreateConnection() => new SqlConnection(_connectionString);

        public async Task<IEnumerable<MigrationRunDto>> GetAllRunsAsync()
        {
            using var conn = CreateConnection();
            const string sql = @"
                SELECT 
                    run_id AS RunId,
                    started_at AS StartedAt,
                    completed_at AS CompletedAt,
                    source_records AS SourceRecords,
                    validated_records AS ValidatedRecords,
                    transformed_records AS TransformedRecords,
                    loaded_records AS LoadedRecords,
                    rejected_records AS RejectedRecords,
                    status AS Status
                FROM MigrationRuns
                ORDER BY started_at DESC;";
            
            return await conn.QueryAsync<MigrationRunDto>(sql);
        }

        public async Task<MigrationRunDto?> GetRunByIdAsync(string runId)
        {
            using var conn = CreateConnection();
            const string sql = @"
                SELECT 
                    run_id AS RunId,
                    started_at AS StartedAt,
                    completed_at AS CompletedAt,
                    source_records AS SourceRecords,
                    validated_records AS ValidatedRecords,
                    transformed_records AS TransformedRecords,
                    loaded_records AS LoadedRecords,
                    rejected_records AS RejectedRecords,
                    status AS Status
                FROM MigrationRuns
                WHERE run_id = @RunId;";
            
            return await conn.QueryFirstOrDefaultAsync<MigrationRunDto>(sql, new { RunId = runId });
        }

        public async Task<IEnumerable<ExceptionDto>> GetExceptionsByRunIdAsync(string runId)
        {
            using var conn = CreateConnection();
            const string sql = @"
                SELECT 
                    exception_id AS ExceptionId,
                    run_id AS RunId,
                    entity_type AS EntityType,
                    record_id AS RecordId,
                    rule_id AS RuleId,
                    severity AS Severity,
                    error_message AS ErrorMessage,
                    source_data AS SourceData,
                    created_at AS CreatedAt,
                    status AS Status
                FROM MigrationExceptions
                WHERE run_id = @RunId
                ORDER BY exception_id ASC;";
            
            return await conn.QueryAsync<ExceptionDto>(sql, new { RunId = runId });
        }

        public async Task<ReconciliationReportDto?> GetReconciliationByRunIdAsync(string runId)
        {
            using var conn = CreateConnection();
            
            // Execute T-SQL Stored Procedure sp_reconcile_migration
            try
            {
                var spResult = await conn.QueryFirstOrDefaultAsync(
                    "sp_reconcile_migration",
                    new { RunId = runId },
                    commandType: CommandType.StoredProcedure);

                if (spResult != null)
                {
                    return new ReconciliationReportDto
                    {
                        RunId = runId,
                        SourceRecords = (int)spResult.source_records,
                        ValidatedRecords = (int)spResult.loaded_records, // Loaded = Validated
                        RejectedRecords = (int)spResult.rejected_records,
                        LoadedRecords = (int)spResult.loaded_records,
                        CountMatch = (int)spResult.source_records == ((int)spResult.loaded_records + (int)spResult.rejected_records),
                        SourceTxnAmount = (decimal)spResult.source_txn_amount,
                        TargetTxnAmount = (decimal)spResult.target_txn_amount,
                        RejectedTxnAmount = (decimal)spResult.rejected_txn_amount,
                        Status = (string)spResult.reconciliation_status
                    };
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Notice calling sp_reconcile_migration: {ex.Message}");
            }

            // Fallback to table query if procedure hasn't executed
            var run = await GetRunByIdAsync(runId);
            if (run == null) return null;

            return new ReconciliationReportDto
            {
                RunId = runId,
                SourceRecords = run.SourceRecords,
                ValidatedRecords = run.ValidatedRecords,
                RejectedRecords = run.RejectedRecords,
                LoadedRecords = run.LoadedRecords,
                CountMatch = run.SourceRecords == (run.ValidatedRecords + run.RejectedRecords),
                Status = run.Status == "COMPLETED" || run.Status == "COMPLETED_WITH_EXCEPTIONS" ? "BALANCED" : "IN_PROGRESS"
            };
        }
    }
}
