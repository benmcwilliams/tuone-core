```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "N_A" or company = "N_A")
sort location, dt_announce desc
```
