## CHANGELOG.md

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.1.0] - 2024-10-04

### Added

- **Azure Login Validation**: The script now checks if the user is logged in to Azure before proceeding. If not logged in, it runs `az login` to prompt for authentication.
- **Interactive Login Prompt**: Allows `az login` to interact with the terminal, ensuring users see the login instructions and can authenticate successfully.
- **Resource Lock Handling**: Automatically removes `CanNotDelete` locks on resource groups before deleting snapshots and restores them afterward.
- **Asynchronous Deletion**: Improved snapshot deletion by making it asynchronous, leading to faster execution times.
- **Enhanced Logging**: Added more detailed logging for better traceability and troubleshooting.

### Changed

- **Error Handling**: Improved error handling for Azure CLI commands to provide more informative feedback to the user.
- **User Prompts**: Updated prompts to be more user-friendly and informative.
- **Code Refactoring**: Cleaned up code for better readability and maintainability.

### Fixed

- **Login Prompt Visibility**: Resolved an issue where the user did not see the `az login` prompt due to subprocess I/O capturing.

## [1.0.0] - 2024-05-31

### Added

- **Initial Release**: Basic functionality to search for snapshots across Azure subscriptions within a specified date range.
- **Keyword Filtering**: Ability to filter snapshots by a keyword in their name.
- **Snapshot Reporting**: Displays detailed information about each snapshot, including name, resource group, creation date, and status.
- **CSV Export**: Option to export snapshot details to a CSV file.
- **Snapshot Deletion**: Identifies old snapshots based on age criteria and allows the user to delete them.
- **Progress Indicators**: Visual progress bars and spinners using the `rich` library.
- **Logging**: Basic logging to a file and console for errors and important events.

```

---

