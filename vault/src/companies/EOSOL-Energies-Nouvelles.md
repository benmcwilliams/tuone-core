```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "EOSOL-Energies-Nouvelles" or company = "EOSOL Energies Nouvelles")
sort location, dt_announce desc
```
