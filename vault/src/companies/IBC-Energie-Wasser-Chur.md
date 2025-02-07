```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "IBC-Energie-Wasser-Chur" or company = "IBC Energie Wasser Chur")
sort location, dt_announce desc
```
