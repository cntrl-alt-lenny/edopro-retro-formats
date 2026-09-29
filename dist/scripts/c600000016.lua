--SPDX-License-Identifier: AGPL-3.0-or-later
--Dice Re-Roll (historical implementation, Retro Formats)
--Upstream: https://github.com/ProjectIgnis/CardScripts/blob/383bfbd62cefc0a28e075acfb78b0bb8203b94c7/official/c83241722.lua
--Copyright (C) 2020  Project Ignis contributors. See version history and author credit line for each file.
--Modified by edopro-retro-formats on 2026-09-29: each activation grants its own re-roll (the once-per-turn record moves from the player to the effect that the activation registers), as the period text names no per-turn limit and the card FAQ lets each activation's effect be used once; the effect description is read from the modern card's strings.
--This modified file is licensed, like its upstream, under the GNU Affero General
--Public License, version 3 or (at your option) any later version. The licence
--text is LICENSE-AGPL-3.0-or-later.txt next to this file in dist/scripts/, and
--LICENSES/AGPL-3.0-or-later.txt in the edopro-retro-formats repository.
--
--Period text: "Once this turn, negate 1 six-sided die roll and re-roll it."
--
--See data/custom-cards/c600000016.json for what this script does not reproduce.
--リバースダイス
--Dice Re-Roll
local s,id=GetID()
function s.initial_effect(c)
	--Activate
	local e1=Effect.CreateEffect(c)
	e1:SetType(EFFECT_TYPE_ACTIVATE)
	e1:SetCode(EVENT_FREE_CHAIN)
	e1:SetOperation(s.regop)
	c:RegisterEffect(e1)
end
function s.regop(e,tp,eg,ep,ev,re,r,rp)
	local e1=Effect.CreateEffect(e:GetHandler())
	e1:SetType(EFFECT_TYPE_FIELD+EFFECT_TYPE_CONTINUOUS)
	e1:SetCode(EVENT_TOSS_DICE_NEGATE)
	e1:SetCondition(s.coincon)
	e1:SetOperation(s.coinop)
	e1:SetReset(RESET_PHASE|PHASE_END)
	Duel.RegisterEffect(e1,tp)
end
function s.coincon(e,tp,eg,ep,ev,re,r,rp)
	return e:GetLabel()==0
end
function s.coinop(e,tp,eg,ep,ev,re,r,rp)
	if e:GetLabel()~=0 then return end
	if Duel.SelectYesNo(tp,aux.Stringid(83241722,0)) then
		Duel.Hint(HINT_CARD,0,id)
		e:SetLabel(1)
		local ct1=(ev&0xff)
		local ct2=(ev>>16)
		Duel.TossDice(ep,ct1,ct2)
	end
end