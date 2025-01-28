```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "AREC-Occitanie" or company = "AREC Occitanie")
sort location, dt_announce desc
```
