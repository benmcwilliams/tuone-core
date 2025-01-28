```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "China-National-Machinery-Import-and-Export-Corporation" or company = "China National Machinery Import and Export Corporation")
sort location, dt_announce desc
```
