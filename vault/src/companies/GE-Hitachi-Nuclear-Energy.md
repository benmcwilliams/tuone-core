```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "GE-Hitachi-Nuclear-Energy" or company = "GE Hitachi Nuclear Energy")
sort location, dt_announce desc
```
