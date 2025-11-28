const evalsPerSecondInput = document.getElementById('evals-per-second');
const policyComplexityInput = document.getElementById('policy-complexity');
const instanceCostInput = document.getElementById('instance-cost');
const calculateButton = document.getElementById('calculate-button');
const monthlyCostOutput = document.getElementById('monthly-cost');

calculateButton.addEventListener('click', () => {
    const evalsPerSecond = parseFloat(evalsPerSecondInput.value);
    const policyComplexity = parseFloat(policyComplexityInput.value);
    const instanceCost = parseFloat(instanceCostInput.value);

    // Assumptions:
    // - A single instance can handle 1000 evaluations per second at 1ms complexity.
    // - The number of instances required scales linearly with evaluations and complexity.
    const instancesNeeded = (evalsPerSecond / 1000) * (policyComplexity / 1);

    const hourlyCost = instancesNeeded * instanceCost;
    const monthlyCost = hourlyCost * 24 * 30;

    monthlyCostOutput.textContent = `$${monthlyCost.toFixed(2)}`;
});