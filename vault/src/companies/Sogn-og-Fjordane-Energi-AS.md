```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Sogn-og-Fjordane-Energi-AS" or company = "Sogn og Fjordane Energi AS")
sort location, dt_announce desc
```
