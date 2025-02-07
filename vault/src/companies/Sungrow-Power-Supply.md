```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sungrow-Power-Supply" or company = "Sungrow Power Supply")
sort location, dt_announce desc
```
