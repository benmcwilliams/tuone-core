```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Smartenergy-Renewables-Deutschland" or company = "Smartenergy Renewables Deutschland")
sort location, dt_announce desc
```
