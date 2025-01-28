```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Eni-New-Energy-SpA" or company = "Eni New Energy SpA")
sort location, dt_announce desc
```
