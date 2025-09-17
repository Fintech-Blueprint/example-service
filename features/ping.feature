Feature: Ping endpoint
  In order to check if the service is alive
  As a system monitor
  I want a /ping endpoint that returns "pong"

  Scenario: Service responds to ping
    Given the service is running
    When I call GET /ping
    Then I receive a 200 OK
    And the body contains "pong"
