```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Trianel-Erneuerbare-Energien" or company = "Trianel Erneuerbare Energien")
sort location, dt_announce desc
```
