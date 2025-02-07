```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "SIG-Swisspower-Stadtwerk" or company = "SIG Swisspower Stadtwerk")
sort location, dt_announce desc
```
