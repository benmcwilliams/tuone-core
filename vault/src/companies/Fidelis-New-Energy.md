```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Fidelis-New-Energy" or company = "Fidelis New Energy")
sort location, dt_announce desc
```
