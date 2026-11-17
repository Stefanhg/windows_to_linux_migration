@desktop
Feature: A familiar Cinnamon desktop across two monitors
  These acceptance tests exercise an already configured desktop.
  They must fail when the behavior is broken even if settings read back correctly.

  Background:
    Given a running Cinnamon X11 desktop with two monitors

  Scenario: Both monitors have a larger taskbar
    Then each monitor has a visible taskbar 60 logical pixels tall

  Scenario Outline: An application's window is available on either taskbar
    Given a new application window
    When I move the application window to monitor <monitor>
    Then the actual application window appears in both taskbars

    Examples:
      | monitor |
      | 0       |
      | 1       |

  Scenario Outline: Pinning an application on either taskbar updates the other
    When I pin an installed application on taskbar <panel>
    Then its launcher appears on both taskbars

    Examples:
      | panel |
      | 0     |
      | 1     |

  Scenario: Dragging a window to the top maximizes it
    Given a new application window
    When I drag its title bar to the top of the monitor
    Then the window fills the monitor work area

  Scenario: The screenshot shortcut opens capture instead of the sound menu
    Given a new application window
    When I press Windows Shift S
    Then a new Flameshot capture overlay is visible
    And the sound menu remains closed
