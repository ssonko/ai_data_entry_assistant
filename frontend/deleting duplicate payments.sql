WITH duplicates AS (
    SELECT 
        transactionNumber,
        employeeId,
        amount,
        checkDate,
        det,
        detCode,
        hours,
        rate,
        transactionType,
        ROW_NUMBER() OVER (
            PARTITION BY 
                transactionNumber,
                employeeId,
                amount,
                checkDate,
                det,
                detCode,
                hours,
                rate,
                transactionType
            ORDER BY transactionNumber
        ) AS rn
    FROM paylocity_ev_payments
)

DELETE FROM duplicates
WHERE rn > 1;