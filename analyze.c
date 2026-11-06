#include <stdio.h>
#include <string.h>

int main() {
    FILE *fp;
    FILE *out;

    char type[20];
    float amount;

    float total_income = 0;
    float total_expense = 0;
    float balance = 0;

    fp = fopen("data.txt", "r");

    if (fp == NULL) {
        out = fopen("result.txt", "w");
        fprintf(out, "Data file not found.\n");
        fclose(out);
        return 1;
    }

    while (fscanf(fp, "%s %f", type, &amount) != EOF) {
        if (strcmp(type, "income") == 0) {
            total_income += amount;
        }
        else if (strcmp(type, "expense") == 0) {
            total_expense += amount;
        }
    }

    fclose(fp);

    balance = total_income - total_expense;

    out = fopen("result.txt", "w");

    fprintf(out, "Total Income: %.2f\n", total_income);
    fprintf(out, "Total Expense: %.2f\n", total_expense);
    fprintf(out, "Remaining Balance: %.2f\n", balance);

    if (total_expense > total_income) {
        fprintf(out, "Status: Overspending Detected\n");
    }
    else {
        fprintf(out, "Status: Within Budget\n");
    }

    fclose(out);

    return 0;
}