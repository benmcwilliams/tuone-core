```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Moray-Offshore-Windfarm-West" or company = "Moray Offshore Windfarm West")
sort location, dt_announce desc
```
