```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Cavalum-SGPS" or company = "Cavalum SGPS")
sort location, dt_announce desc
```
