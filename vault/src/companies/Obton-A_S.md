```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Obton-A_S" or company = "Obton A_S")
sort location, dt_announce desc
```
