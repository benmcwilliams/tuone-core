```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Zentrum-für-Sonnenenergie-und-Wasserstoff-Forschung-Baden-Württemberg" or company = "Zentrum für Sonnenenergie und Wasserstoff Forschung Baden Württemberg")
sort location, dt_announce desc
```
