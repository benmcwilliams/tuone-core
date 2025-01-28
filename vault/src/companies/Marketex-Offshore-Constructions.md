```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Marketex-Offshore-Constructions" or company = "Marketex Offshore Constructions")
sort location, dt_announce desc
```
