```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Solarenergie-Boitzenburger-Land" or company = "Solarenergie Boitzenburger Land")
sort location, dt_announce desc
```
