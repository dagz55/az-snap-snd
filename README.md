# Azure Snapshot Search and Destroy


![Azure](https://img.shields.io/badge/Azure-Snapshot%20Search%20and%20Destroy-blue)
![Python](https://img.shields.io/badge/Python-3.7%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

![GitHub forks](https://img.shields.io/github/forks/dagz55/Azure-Snapshot%20Search%20and%20Destroy-blue?style=social)
![GitHub stars](https://img.shields.io/github/stars/dagz55/Azure-Snapshot%20Search%20and%20Destroy-blue?style=social)
```markdown

The **Azure Snapshot Search and Destroy** is a powerful, interactive tool designed and created by Robert Suarez [rsuar29@albertsons.com] to streamline the management of Azure VM snapshots across all your subscriptions. It automates the process of searching, reporting, and cleaning up snapshots, saving you time and reducing cloud costs.

## ✨ Features

- **Automatic Azure Login Validation**: Checks if you're logged in to Azure and prompts for login if necessary.
- **Multi-Subscription Support**: Searches snapshots across all Azure subscriptions associated with your account.
- **Interactive Date Range Selection**: Allows you to specify custom start and end dates for snapshot searches.
- **Keyword Filtering**: Filters snapshots based on a user-provided keyword.
- **Detailed Reporting**: Displays comprehensive details about each snapshot, including name, resource group, creation date, age, creator, and status.
- **Color-Coded Age Indicators**: Uses color coding to highlight snapshots based on their age (e.g., green for recent, red for old).
- **CSV Export**: Exports snapshot details to a CSV file for further analysis or record-keeping.
- **Automated Deletion**: Identifies and deletes old snapshots based on customizable age criteria for production and non-production environments.
- **Resource Lock Handling**: Automatically removes and restores resource locks to ensure smooth deletion of snapshots.
- **Asynchronous Operations**: Utilizes Python's asyncio for efficient, non-blocking execution.
- **User-Friendly Interface**: Leverages the `rich` library for an interactive and visually appealing console experience.
- **Comprehensive Logging**: Generates detailed logs for troubleshooting and audit purposes.

## 📋 Requirements

- **Python 3.7 or higher**
- **Azure CLI (`az`)**: Installed and configured on your system.
- **Python Packages**: Install the required packages using the command below.

### Install Required Python Packages

```bash
pip install rich asyncio
```

## 🚀 Getting Started

### Clone the Repository

```bash
git clone https://github.albertsons.com/rsuar29/azure-snapshot-snd.git
cd azure-snapshot-snd
```

### Run the Script

```bash
python azure-snapshot-search-and-destroy.py
```

## 🛠 How to Use

1. **Run the Script**: Execute `python azure_snapshot_snd.py` in your terminal.

2. **Azure Login**: If not logged in, the script will prompt you to log in to Azure.

   ```plaintext
   You are not logged in to Azure. Please log in.

   To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code ABCD-EFGH to authenticate.
   ```

3. **Enter Date Range**: Provide the start and end dates for the snapshot search.

   ```plaintext
   Enter start date (YYYY-MM-DD) [default: 2023-10-01]:
   Enter end date (YYYY-MM-DD) [default: 2023-10-31]:
   ```

4. **Keyword Filtering**: Optionally, enter a keyword to filter snapshots. Optional in this case, but can be used to filter out snapshots by name. This is useful if you have a naming convention that includes a keyword that you want to filter out. 

   ```plaintext
   Enter a keyword to filter snapshots (optional):
   ```

5. **View Results**: The script will display snapshots matching your criteria, along with detailed information.

6. **Export to CSV**: Choose whether to export the results to a CSV file.

   ```plaintext
   Do you want to export results to CSV? [y/n] y
   ```

7. **Automated Deletion**: The script identifies snapshots eligible for deletion based on their age and environment (production or non-production).

   ```plaintext
   There are 5 non-prod snapshots that are 3 days or older.
   Do you want to delete these snapshots? [y/n] y
   ```

8. **Completion**: Upon completion, the script provides a summary of actions taken.

   ```plaintext
   Snapshot search and destroy complete!
   ```

## 🎯 Use Cases

- **Cost Optimization**: Remove old and unnecessary snapshots to reduce Azure storage costs.
- **Compliance**: Maintain compliance by ensuring that snapshots are retained or deleted according to your organization's policies.
- **Automation**: Save time by automating routine snapshot management tasks.

## ⚙️ Configuration

- **Age Criteria**: Modify the `age_limit` variable in the script to change the age threshold for snapshot deletion.
- **Environment Detection**: Adjust the `is_non_prod()` and `is_prod()` functions to match your organization's naming conventions for subscriptions.

## 📄 Logging

- **Log File**: The script generates a log file named `azure_snapshot_manager_YYYYMMDD_username.log`.
- **Log Level**: Logging is set to `ERROR` by default. You can change the logging level in the script's configuration to `INFO` or `DEBUG` for more detailed logs.

## 🖥 Tested Environments

- **Operating Systems**: Windows 10, macOS Catalina, Ubuntu 20.04
- **Python Versions**: Python 3.7, 3.8, 3.9

## 🐛 Troubleshooting

- **Azure CLI Not Found**: Ensure that the Azure CLI is installed and added to your system's PATH.
- **Authentication Issues**: If you encounter issues during login, try running `az login` manually to diagnose the problem.
- **Insufficient Permissions**: Make sure your Azure account has the necessary permissions to list and delete snapshots.

## 📬 Support

For any questions or issues, please open an issue on the [GitHub repository](https://github.albertsons.com/rsuar29/azure-snapshot-snd/issues) or contact [Robert Suarez](mailto:rsuar29@albertsons.com).

## 🤝 Contributing

We welcome contributions! Please read our [contribution guidelines](CONTRIBUTING.md) before submitting a pull request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
```
