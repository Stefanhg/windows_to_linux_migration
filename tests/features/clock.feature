@desktop @clock
Feature: Both taskbars display the time
  Scenario: A visible clock is rendered on each monitor
    Given a running Cinnamon X11 desktop with two monitors
    Then both taskbars render their current clock text
