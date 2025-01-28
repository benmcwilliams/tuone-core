```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Nantes-–-Saint-Nazaire-Port" or company = "Nantes – Saint Nazaire Port")
sort location, dt_announce desc
```
