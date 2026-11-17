@desktop @task-manager
Feature: Windows Task Manager maps to Mission Center
  Background:
    Given Mission Center is installed
    And Mission Center is ready to launch

  Scenario: The Task Manager application launcher opens Mission Center
    Given a searchable Task Manager application launcher exists
    When I launch Task Manager
    Then a Mission Center window is visible

  Scenario: The Windows Task Manager shortcut opens Mission Center
    When I press Control Shift Escape
    Then a Mission Center window is visible
