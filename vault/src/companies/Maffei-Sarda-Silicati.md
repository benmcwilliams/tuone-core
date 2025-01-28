```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Maffei-Sarda-Silicati" or company = "Maffei Sarda Silicati")
sort location, dt_announce desc
```
