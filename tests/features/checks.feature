Feature Checks Management
  In order to manage checks
  As a financial account clerk
  I have to create, delete, update, search for checks

  Scenario Outline: Creation of a Check
    Given I have a <formula>
    And I have a unique <name>
    And I have a <tolerance>
    And I have an <operator>
    When I create it on the system
    Then I can look after it by <name> 

    Examples:
    | formula | name | operator | tolerance |
    | A=B-C   | ckA  | <        |       0.1 |
    | A=B+C   | ckA  | >        |         1 |
