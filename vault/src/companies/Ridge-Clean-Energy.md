```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Ridge-Clean-Energy" or company = "Ridge Clean Energy")
sort location, dt_announce desc
```
