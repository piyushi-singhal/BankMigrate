using System;
using System.Collections.Generic;

namespace BankMigrate.Api.Models
{
    public class MigrationRunDto
    {
        public string RunId { get; set; } = string.Empty;
        public DateTime StartedAt { get; set; }
        public DateTime? CompletedAt { get; set; }
        public int SourceRecords { get; set; }
        public int ValidatedRecords { get; set; }
        public int TransformedRecords { get; set; }
        public int LoadedRecords { get; set; }
        public int RejectedRecords { get; set; }
        public string Status { get; set; } = string.Empty;
    }

    public class ExceptionDto
    {
        public int ExceptionId { get; set; }
        public string RunId { get; set; } = string.Empty;
        public string EntityType { get; set; } = string.Empty;
        public string? RecordId { get; set; }
        public string RuleId { get; set; } = string.Empty;
        public string Severity { get; set; } = string.Empty;
        public string ErrorMessage { get; set; } = string.Empty;
        public string? SourceData { get; set; }
        public DateTime CreatedAt { get; set; }
        public string Status { get; set; } = string.Empty;
    }

    public class ReconciliationReportDto
    {
        public string RunId { get; set; } = string.Empty;
        public int SourceRecords { get; set; }
        public int ValidatedRecords { get; set; }
        public int RejectedRecords { get; set; }
        public int LoadedRecords { get; set; }
        public bool CountMatch { get; set; }
        public decimal SourceTxnAmount { get; set; }
        public decimal TargetTxnAmount { get; set; }
        public decimal RejectedTxnAmount { get; set; }
        public string Status { get; set; } = string.Empty;
    }

    public class StartMigrationRequest
    {
        public string? RunId { get; set; }
    }

    public class StartMigrationResponse
    {
        public string RunId { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
    }
}
