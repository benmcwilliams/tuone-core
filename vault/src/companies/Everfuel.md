```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Everfuel" or company = "Everfuel")
sort location, dt_announce desc
```
