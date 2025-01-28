```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Kabel-Premium-Pulp-&-Paper-GmbH" or company = "Kabel Premium Pulp & Paper GmbH")
sort location, dt_announce desc
```
