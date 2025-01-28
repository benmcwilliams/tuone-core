```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Deutsches-Zentrum-fuer-Luft--und-Raumfahrt-e.V." or company = "Deutsches Zentrum fuer Luft  und Raumfahrt e.V.")
sort location, dt_announce desc
```
