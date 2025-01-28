```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "PRF-Gas-Solutions" or company = "PRF Gas Solutions")
sort location, dt_announce desc
```
