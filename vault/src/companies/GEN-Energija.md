```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Gen-Energija" or company = "Gen Energija")
sort location, dt_announce desc
```
