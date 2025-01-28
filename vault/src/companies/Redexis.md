```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Redexis" or company = "Redexis")
sort location, dt_announce desc
```
