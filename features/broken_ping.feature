Feature: Broken Ping Service
  Scenario: Broken ping missing Then
    Given the service is running
    When I send "ping"
