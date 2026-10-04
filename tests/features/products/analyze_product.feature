Feature: Product Analysis
  As a dropshipping operator
  I want to analyze Dropi products automatically
  So that I can identify the most profitable ones to sell

  Background:
    Given the ProductAnalystAgent is initialized

  Scenario: Analyze a product with good margin and sufficient stock
    Given a product with dropi_price 18.00 and suggested_price 35.00 and stock 25
    When I analyze the product
    Then the margin should be approximately 48.57 percent
    And the recommendation should be BUY or WATCH
    And the total score should be between 0.0 and 100.0

  Scenario: Skip product with insufficient margin (CA-PROD-01)
    Given a product with dropi_price 8.00 and suggested_price 9.50 and stock 100
    When I analyze the product
    Then the margin should be less than 25.0 percent
    And the recommendation should be SKIP

  Scenario: Downgrade BUY to WATCH for low stock (CA-PROD-03)
    Given a product with dropi_price 20.00 and suggested_price 55.00 and stock 3
    When I analyze the product
    Then the recommendation should not be BUY
    And the total score should be less than 70.0

  Scenario: Score 75 requires BUY recommendation (CA-PROD-02)
    Given a product with a score of 75
    Then the recommendation must be BUY

  Scenario: Score 55 requires WATCH recommendation (CA-PROD-02)
    Given a product with a score of 55
    Then the recommendation must be WATCH

  Scenario: Score 30 requires SKIP recommendation (CA-PROD-02)
    Given a product with a score of 30
    Then the recommendation must be SKIP
