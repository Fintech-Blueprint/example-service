Feature: Ping Service
  As a client
  I want to ping the service
  So that I receive a pong response

  Scenario: Successful ping
    Given the service is running
    When I send "ping"
    Then I receive "pong"
Feature: Ping

  Scenario: Ping returns pong
    Given the service is running
    When a client calls /ping
    Then the service responds with "pong"
Feature: Ping endpoint
  In order to check if the service is alive
  As a system monitor
  I want a /ping endpoint that returns "pong"

  Scenario: Service responds to ping
    Given the service is running
    When I call GET /ping
    Then I receive a 200 OK
    And the body contains "pong"
